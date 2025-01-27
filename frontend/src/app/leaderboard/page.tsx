"use client"

import LeaderList, { Leader } from '@/components/LeaderList';
import React, { useState, useEffect } from 'react';

type Leaderboard = {
    threat: Leader[];
    nice: Leader[];
}

function Leaderboard() {
    const [data, setData] = useState<Leaderboard | null>(null);

    const fetchLeaderboard = () => {
        fetch('http://localhost:8000/leaderboard')
            .then(response => response.json())
            .then(data => setData(data))
            .catch(error => console.error("Error fetching leaderboard:", error));
    }

    useEffect(() => {
        const intervalId = setInterval(() => {
            fetchLeaderboard();
        }, 5000);

        return () => clearInterval(intervalId);
    }, []);

    const handleNameChange = (newName: string, id: string) => {
        fetch('http://localhost:8000/update-name', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id: id, name: newName })
        })
        .catch(error => console.error('Error updating name:', error));
    };

    if (!data) return null;
    return (
        <div className={`absolute w-screen h-screen overflow-hidden flex flex-col justify-evenly items-center bg-background font-mono`}>
            <p className={`text-foreground font-bold text-center text-8xl`}>THREAT LEADERBOARD</p>
            <div className={`flex gap-10 justify-center items-center`}>
                <div className="flex items-center just h-full">
                    <p
                        className="text-foreground text-center text-7xl transform -rotate-90 whitespace-nowrap"
                        style={{ width: '100px' }}
                    >
                        HIGH
                    </p>
                </div>
                <LeaderList 
                    items={data.threat} 
                    handleNameChange={handleNameChange}
                />
            </div>
            <div className={`flex gap-10 justify-center items-center`}>
                <div className="flex items-center h-full">
                    <p
                        className="text-foreground text-center text-7xl transform -rotate-90 whitespace-nowrap"
                        style={{ width: '100px' }}
                    >
                        LOW
                    </p>
                </div>
                <LeaderList 
                    items={data.nice} 
                    handleNameChange={handleNameChange}
                />
            </div>
        </div>
    );
}

export default Leaderboard;