'use client';

import React, { useState, useEffect } from 'react';

const CameraFeed = () => {
    const [src, setSrc] = useState('');

    useEffect(() => {
        // Ensure the cache buster updates only on the client side
        setSrc(`http://localhost:8000/video_feed?cache_buster=${Date.now()}`);
    }, []);

    if (!src) return null; // Avoid rendering on the server

    return (
        <img
            className="w-full pl-5 max-h-[50vh] object-contain"
            src={src}
            alt="Webcam Feed"
        />
    );
};

export default CameraFeed;