"use client"

import React, { useState, useEffect, useCallback, forwardRef, useImperativeHandle, ForwardedRef } from 'react';

interface AlarmOverlayProps {
    audioUrl?: string;
}

interface AlarmOverlayRef {
    trigger: () => void;
}

const AlarmOverlay = forwardRef(({ audioUrl = '' }: AlarmOverlayProps, ref: ForwardedRef<AlarmOverlayRef>) => {
    const [isVisible, setIsVisible] = useState<boolean>(false);
    const [audio] = useState<HTMLAudioElement>(() => new Audio(audioUrl));

    useEffect(() => {
        // Preload audio
        if (audioUrl) {
            audio.load();
        }
        return () => {
            audio.pause();
            audio.currentTime = 0;
        };
    }, [audio, audioUrl]);

    const trigger = useCallback(() => {
        let flashCount = 0;
        const maxFlashes = 3;
        const flashDuration = 1000; // milliseconds
        const darkDuration = 300; // milliseconds

        const flash = () => {
            if (flashCount < maxFlashes) {
                setIsVisible(true);
                if (audioUrl) {
                    audio.currentTime = 0;
                    audio.play().catch(error => {
                        console.warn('Audio playback failed:', error);
                    });
                }

                setTimeout(() => {
                    setIsVisible(false);
                    audio.pause();
                    audio.currentTime = 0;
                    setTimeout(() => {
                        flashCount++;
                        flash();
                    }, darkDuration);
                }, flashDuration);
            }
        };

        flash();
    }, [audio, audioUrl]);

    useImperativeHandle(ref, () => ({
        trigger
    }));

    if (!isVisible) return null;

    return (
        <div className="fixed inset-0 bg-red-500 bg-opacity-50 flex items-center justify-center z-50 animate-pulse">
            <h1 className="text-white text-8xl font-bold">ALARM</h1>
        </div>
    );
});

AlarmOverlay.displayName = 'AlarmOverlay';

// Type for the hook return value
interface UseAlarmReturn {
    AlarmComponent: React.ReactElement | null;
    triggerAlarm: () => void;
}

// Create a hook to use the alarm
const useAlarm = (audioUrl: string = ''): UseAlarmReturn => {
    const [alarmComponent, setAlarmComponent] = useState<React.ReactElement | null>(null);
    const alarmRef = React.useRef<AlarmOverlayRef | null>(null);

    useEffect(() => {
        const component = <AlarmOverlay ref={alarmRef} audioUrl={audioUrl} />;
        setAlarmComponent(component);
    }, [audioUrl]);

    const triggerAlarm = useCallback(() => {
        if (alarmRef.current) {
            alarmRef.current.trigger();
        }
    }, []);

    return { AlarmComponent: alarmComponent, triggerAlarm };
};

export type { AlarmOverlayProps, AlarmOverlayRef };
export { AlarmOverlay, useAlarm };