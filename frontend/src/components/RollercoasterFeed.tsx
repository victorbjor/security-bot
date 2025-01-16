"use client"

import React, {useEffect, useRef, useState} from "react";

type DecisionAnswer = {
    description: string
    higher_level_reasoning: string
    escalation_level: string
    escalation_reason: string
}


type FeedMessage = {
    decision: DecisionAnswer,
    date: string,
    image: string
}

const MAX_DETECTIONS = 4;

const ESCALATION_LEVELS = {
    'THE PERSON IS NOT A THREAT': 'False Positive',
    'THE PERSON IS NOT AN IMMEDIATE THREAT, BUT SHOULD BE LOGGED': 'Log',
    'THE PERSON IS AN IMMEDIATE THREAT, AND SECURITY SHOULD BE CALLED': 'Alert Security',
    'THE PERSON IS AN IMMEDIATE THREAT, AND THE GENERAL ALARM SHOULD BE TRIGGERED': 'Alarm!'
}


const RollercoasterFeed = () => {
    const [detections, setDetections] = useState<(FeedMessage | null)[]>(Array(MAX_DETECTIONS).fill(null));
    const nextIdx = useRef(0);

    useEffect(() => {
        const ws = new WebSocket("ws://localhost:8000/ws/verdicts");

        ws.onmessage = (event) => {
            const rawData = JSON.parse(event.data);
            const data: FeedMessage = {
                image: rawData.image,
                decision: JSON.parse(rawData.decision),
                date: new Date().toLocaleTimeString('en-US', { hour12: false })
            };
            console.log(data.decision.description);
            setDetections(prevDetections => {
                const newDetections = [...prevDetections];
                newDetections[nextIdx.current] = {
                    image: data.image,
                    decision: data.decision,
                    date: data.date
                };
                nextIdx.current = (nextIdx.current + 1) % (MAX_DETECTIONS);
                return newDetections.slice(0, MAX_DETECTIONS);
            });
        };

        ws.onopen = () => {
            console.log("WebSocket connected for detections feed");
        };

        ws.onclose = () => {
            console.log("WebSocket disconnected");
        };

        return () => {
            ws.close();
        };
    }, []);

    return (
        <div className="flex flex-col w-full h-screen items-center justify-center">
            <p className="text-foreground text-2xl">Detection Feed</p>
            <div className="grid grid-rows-2 grid-cols-2 gap-4 pr-4 w-full">
                {detections.map((detection, index) => (
                    detection && (
                        <div key={index} className="border border-shade rounded-md p-4">
                            <div className="aspect-square w-full">
                                <img src={detection.image} alt={`Detection ${index}`} className="w-full h-full object-contain" />
                            </div>
                            <p className="text-xs text-gray-500 italic pb-1">{detection.date}</p>
                            <p className="text-md font-bold text-gray-800">{ESCALATION_LEVELS[detection.decision.escalation_level as keyof typeof ESCALATION_LEVELS]}</p>
                            <p className="text-xs text-gray-500">{detection.decision.escalation_reason}</p>
                        </div>
                    )
                ))}
            </div>
        </div>
    );
};

export default RollercoasterFeed;