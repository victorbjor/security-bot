import React from 'react';

const CameraFeed = () => {
    return (
        // <div className={`flex flex-col w-full h-72 items-center justify-center`}>
            <img
                className={'w-full pl-5 max-h-[50vh] object-contain'}
                src={`http://localhost:8000/video_feed?cache_buster=${Date.now()}`} // URL to the MJPEG feed
                alt="Webcam Feed"
            />
        // </div>
    );
};

export default CameraFeed;