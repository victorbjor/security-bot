"use client"

import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

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

const ESCALATION_LEVELS = {
    'THE PERSON IS NOT A THREAT': 'False Positive',
    'THE PERSON IS NOT AN IMMEDIATE THREAT, BUT SHOULD BE LOGGED': 'Log',
    'THE PERSON IS AN IMMEDIATE THREAT, AND SECURITY SHOULD BE CALLED': 'Alert Security',
    'THE PERSON IS AN IMMEDIATE THREAT, AND THE GENERAL ALARM SHOULD BE TRIGGERED': 'Alarm!'
}

const RollercoasterFeed = () => {
    const [leftColumn, setLeftColumn] = useState<FeedMessage[]>([]);
    const [rightColumn, setRightColumn] = useState<FeedMessage[]>([]);
    const [leftNext, setLeftNext] = useState(true);

    useEffect(() => {
        const ws = new WebSocket("ws://localhost:8000/ws/verdicts");

        ws.onmessage = (event) => {
            const rawData = JSON.parse(event.data);
            const data: FeedMessage = {
                image: rawData.image,
                decision: JSON.parse(rawData.decision),
                date: new Date().toLocaleTimeString('en-US', { hour12: false })
            };

            if (leftNext) {
                setLeftColumn(prev => [data, ...prev].slice(0, 3));
            } else {
                setRightColumn(prev => [data, ...prev].slice(0, 3));
            }
            setLeftNext(!leftNext);
        };

        ws.onopen = () => console.log("WebSocket connected for detections feed");
        ws.onclose = () => console.log("WebSocket disconnected");
        return () => ws.close();
    }, []);

    const cardVariants = {
        initial: { opacity: 0, y: -20 },
        animate: { opacity: 1, y: 0 },
        exit: { opacity: 0, y: 20 }
    };

    const DetectionCard = ({ detection, index }: { detection: FeedMessage, index: number }) => (
        <motion.div
            layout
            initial="initial"
            animate="animate"
            exit="exit"
            variants={cardVariants}
            transition={{ duration: 0.3 }}
            style={{ originY: 0 }}
            className="border border-shade rounded-md p-4 mb-4"
        >
            {/*<motion.div className="aspect-square w-full" layoutId={`image-${detection.date}`}>*/}
                <img src={detection.image} alt="Detection" className="w-full h-full object-contain" />
            {/*</motion.div>*/}
            <p className="text-xs text-gray-500 italic pb-1">{detection.date}</p>
            <p className="text-md font-bold text-gray-800">
                {ESCALATION_LEVELS[detection.decision.escalation_level as keyof typeof ESCALATION_LEVELS]}
            </p>
            <p className="text-xs text-gray-500">{detection.decision.escalation_reason}</p>
        </motion.div>
    );

    return (
        <div className="flex flex-col w-full h-screen items-center justify-center">
            <p className="text-foreground text-2xl mb-4">Detection Feed</p>
            <div className="flex gap-4 w-full max-w-4xl px-4">
                <div className="flex-1">
                    <AnimatePresence>
                        {leftColumn.map((detection, index) => (
                            <DetectionCard key={detection.date} detection={detection} index={index} />
                        ))}
                    </AnimatePresence>
                </div>
                <div className="flex-1">
                    <AnimatePresence>
                        {rightColumn.map((detection, index) => (
                            <DetectionCard key={detection.date} detection={detection} index={index} />
                        ))}
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
};

export default RollercoasterFeed;