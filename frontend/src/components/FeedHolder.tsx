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
    'THE IMAGE IS NOT READABLE': 'Not Readable',
    'THE PERSON IS NOT A THREAT': 'False Positive',
    'THE PERSON IS NOT AN IMMEDIATE THREAT, BUT SHOULD BE LOGGED': 'Log',
    'THE PERSON IS AN IMMEDIATE THREAT, AND SECURITY SHOULD BE CALLED': 'Alert Security',
    'THE PERSON IS AN IMMEDIATE THREAT, AND THE GENERAL ALARM SHOULD BE TRIGGERED': 'Alarm!'
}

type Props = {
    onAlarm: ()=>void
}

export const FeedHolder = ({onAlarm}: Props) => {
    const [discardCards, setDiscardCards] = useState<FeedMessage[]>([]);
    const [logCards, setLogCards] = useState<FeedMessage[]>([]);
    const [threatCards, setThreatCards] = useState<FeedMessage[]>([]);

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
            // data.decision.escalation_level = ESCALATION_LEVELS[data.decision.escalation_level as keyof typeof ESCALATION_LEVELS]

            switch (data.decision.escalation_level) {
                case 'Log':
                    setLogCards(prevCards => [data, ...prevCards]);
                    break;
                case 'False Positive':
                    setDiscardCards(prevCards => [data, ...prevCards]);
                    break;
                case 'Not Readable':
                    setDiscardCards(prevCards => [data, ...prevCards]);
                    break;
                case 'Call Security':
                    setThreatCards(prevCards => [data, ...prevCards]);
                    break;
                case 'Alarm':
                    onAlarm();
                    setThreatCards(prevCards => [data, ...prevCards]);
                    break;
                default:
                    console.error('Unknown decision', data.decision.escalation_level);
            }
        };

        ws.onopen = () => console.log("WebSocket connected for detections feed");
        ws.onclose = () => console.log("WebSocket disconnected");
        return () => ws.close();
    }, []);

    return (
        <div className="flex flex-row w-1/2 items-center">
            <ProductBoard title={"Detected Threats"} cards={threatCards}/>
            <ProductBoard title={"Log"} cards={logCards}/>
            <ProductBoard title={"Discarded"} cards={discardCards}/>
        </div>
    );
};