"use client"

import React, {useEffect, useRef, useState} from "react";
import {FeedMessage} from "@/components/FeedHolder";

type Props = {
    title: string;
    cards: FeedMessage[]
}

interface Dimensions {
    width: number;
    height: number;
}

const ProductBoard = ({title, cards}: Props) => {
    return (
        <div className="flex flex-col w-full h-screen items-center justify-start">
            <p className="text-foreground text-2xl">{title}</p>
            <div className="w-full max-w-4xl mx-auto p-4">
                <div className="relative">
                    {cards.length === 0 ? (
                        <div className="w-full bg-white rounded-lg shadow-lg p-8 text-center">
                            <p className="text-gray-500">Feed is empty</p>
                        </div>
                    ) : (
                        cards.map((card, index) => (
                            <div
                                key={card.id}
                                className="absolute w-full left-0 bg-white rounded-lg shadow-lg overflow-hidden transition-all duration-500 ease-in-out"
                                style={{
                                    transform: `translateY(${index * 300}px)`,
                                    opacity: index < 5 ? 1 : 0,
                                    pointerEvents: index < 5 ? 'auto' : 'none'
                                }}
                            >
                                <div key={`${card.date}-${index}`} className="border rounded-md max-h-[300px]">
                                    {/*<div className="aspect-square w-full">*/}
                                    <div className="w-full pb-2">
                                        <img src={card.image} alt={`Detection ${index}`}
                                             className="w-full max-h-[150px] object-contain"/>
                                    </div>
                                    <p className="text-xs text-gray-500 italic pb-1 px-1">{card.date}</p>
                                    <p className="text-md font-bold text-gray-800 px-1">{card.decision.escalation_level}</p>
                                    <p className="text-xs text-gray-500 p-1 overflow-ellipsis">{card.decision.escalation_reason}</p>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

export default ProductBoard;