import React, { useState } from 'react';

export type Leader = {
    id: string,
    score: number,
    image: string,
    name: string,
};

type Props = {
    items: Leader[]
    handleNameChange: (name: string, id: string) => void;
}

const LeaderList = ({ items, handleNameChange }: Props) => {
  // Local state for input values
  const [inputValues, setInputValues] = useState<{ [key: string]: string }>({});

  const handleInputChange = (value: string, id: string) => {
    setInputValues(prev => ({
      ...prev,
      [id]: value
    }));
  };

  const handleSubmit = (id: string) => {
    const newName = inputValues[id];
    if (newName !== undefined && newName !== items.find(item => item.id === id)?.name) {
      handleNameChange(newName, id);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>, id: string) => {
    if (e.key === 'Enter') {
      handleSubmit(id);
      e.currentTarget.blur();
    }
  };
  
  return (
    <div className="flex p-6 border-l border-b border-black/30">
        {items.map((item: Leader, index   ) => (
            <div
            key={item.id}
            className="flex flex-col items-center justify-center p-2 gap-2"
            >
                <p>{index+1}</p>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                src={item.image}
                alt={`${item.name}'s avatar`}
                className="w-60 h-60 rounded-sm object-contain" // Ensure full image fits
                />

                <div className="flex-grow">
                <input
                    type="text"
                    value={
                    inputValues[item.id] === undefined
                        ? item.name
                        : inputValues[item.id]
                    }
                    onChange={(e) => handleInputChange(e.target.value, item.id)}
                    onBlur={() => handleSubmit(item.id)}
                    onKeyDown={(e) => handleKeyDown(e, item.id)}
                    className="border p-2 w-full max-w-md text-center bg-transparent"
                    placeholder="Unknown"
                />
                </div>

                <p className="text-gray-700 min-w-[80px] text-center">{(item.score * 100).toFixed(1)} %</p>
            </div>
    ))}
    </div>
  );
};

export default LeaderList;