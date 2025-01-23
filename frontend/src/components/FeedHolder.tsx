"use client"

import ProductBoard from "@/components/ProductBoard";
import {useEffect, useState} from "react";

type DecisionAnswer = {
    description: string
    higher_level_reasoning: string
    escalation_level: string
    escalation_reason: string
}

export type FeedMessage = {
    id: number,
    decision: DecisionAnswer,
    date: string,
    image: string
}

const ESCALATION_LEVELS = {
    'THE PERSON IS NOT A THREAT': 'False Positive',
    'THE PERSON IS NOT AN IMMEDIATE THREAT, BUT SHOULD BE LOGGED': 'Log',
    'THE PERSON IS AN IMMEDIATE THREAT, AND SECURITY SHOULD BE CALLED': 'Alert Security',
    'THE PERSON IS AN IMMEDIATE THREAT, AND THE GENERAL ALARM SHOULD BE TRIGGERED': 'Alarm!'
}

export const FeedHolder = () => {
    const [lowCards, setLowCards] = useState<FeedMessage[]>([]);
    const [highCards, setHighCards] = useState<FeedMessage[]>([]);

    const addCard = (feedMessage: FeedMessage, highThreat: boolean) => {
        if (highThreat) {
            setHighCards(prevCards => [feedMessage, ...prevCards]);
        } else {
            setLowCards(prevCards => [feedMessage, ...prevCards]);
        }
    };

    useEffect(() => {
        const ws = new WebSocket("ws://localhost:8000/ws/verdicts");

        ws.onmessage = (event) => {

            const rawData = JSON.parse(event.data);
            const data: FeedMessage = {
                id: Date.now(),
                image: rawData.image,
                decision: JSON.parse(rawData.decision),
                date: new Date().toLocaleTimeString('en-US', { hour12: false })
            };
            data.decision.escalation_level = ESCALATION_LEVELS[data.decision.escalation_level as keyof typeof ESCALATION_LEVELS]

            switch (data.decision.escalation_level) {
                case 'Log':
                    addCard(data, false);
                    break;
                case 'False Positive':
                    addCard(data, false);
                    break;
                case 'Alert Security':
                    addCard(data, true);
                    break;
                case 'Alarm!':
                    addCard(data, true);
                    break;
                default:
                    console.error('Unknown decision', data.decision.escalation_level);
            }


            // if (leftNext) {
            //     setLeftColumn(prev => [data, ...prev].slice(0, 3));
            // } else {
            //     setRightColumn(prev => [data, ...prev].slice(0, 3));
            // }
            // setLeftNext(!leftNext);
        };

        ws.onopen = () => console.log("WebSocket connected for detections feed");
        ws.onclose = () => console.log("WebSocket disconnected");
        return () => ws.close();
    }, []);

    return (
        <div className="flex flex-row w-1/3 items-center">
            <ProductBoard title={"Low Threat Feed"} cards={lowCards}/>
            <ProductBoard title={"High Threat Feed"} cards={highCards}/>
        </div>
    );
};