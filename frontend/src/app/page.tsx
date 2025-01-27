"use client"

import CameraFeed from "@/components/CameraFeed";
import {FeedHolder} from "@/components/FeedHolder";
import {useAlarm} from "@/components/AlarmOverlay";

export default function Home() {
    const { AlarmComponent, triggerAlarm } = useAlarm('/error_sound-221445.mp3');

    return (
        <div className={`absolute w-screen h-screen overflow-hidden flex justify-around items-center bg-background font-mono`}>
            <div className="flex flex-row w-full items-center gap-10">
                <div className="flex flex-col w-1/2 gap-10 items-center">
                    <p className="text-foreground text-center text-8xl">Security Bot</p>
                    <CameraFeed />
                </div>
                <FeedHolder onAlarm={triggerAlarm} />
            </div>
            {AlarmComponent}
        </div>
  );
}
