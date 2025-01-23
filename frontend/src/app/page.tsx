import CameraFeed from "@/components/CameraFeed";
import RollercoasterFeed from "@/components/RollercoasterFeed";
import ProductBoard from "@/components/ProductBoard";
import {FeedHolder} from "@/components/FeedHolder";

export default function Home() {
  return (
    <div className={`absolute w-full h-full overflow-hidden flex justify-around items-center bg-background font-mono`}>
      <div className="flex flex-row items-center gap-10">
        <div className="flex flex-col w-2/3 gap-10 items-center">
          <p className="text-foreground text-center text-8xl">Security Bot</p>
          <CameraFeed />
        </div>
        <FeedHolder />
      </div>
    </div>
  );
}
