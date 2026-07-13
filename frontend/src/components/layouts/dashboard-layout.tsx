import { useEffect, useState } from "react";
import { useNavigation } from "react-router";

import logo from "@/assets/logo.svg";
import { paths } from "@/config/paths";

import { Link } from "../ui/link";

const Logo = () => {
  return (
    <Link className="flex items-center gap-2 text-white" to={paths.home.getHref()}>
      <img className="h-8 w-auto" src={logo} alt="" />
      <span className="text-sm font-semibold text-white">HOS Trip Planner</span>
    </Link>
  );
};

/** Thin top loading bar driven by router navigation state. */
const Progress = () => {
  const { state, location } = useNavigation();
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    setProgress(0);
  }, [location?.pathname]);

  useEffect(() => {
    if (state === "loading") {
      const timer = setInterval(() => {
        setProgress((oldProgress) => {
          if (oldProgress === 100) {
            clearInterval(timer);
            return 100;
          }
          return Math.min(oldProgress + 10, 100);
        });
      }, 300);
      return () => clearInterval(timer);
    }
  }, [state]);

  if (state !== "loading") {
    return null;
  }

  return (
    <div
      className="fixed left-0 top-0 z-40 h-1 bg-blue-500 transition-all duration-200 ease-in-out"
      style={{ width: `${progress}%` }}
    />
  );
};

export function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen w-full flex-col bg-muted/40">
      <Progress />
      <header className="sticky top-0 z-30 border-b bg-slate-900">
        <div className="mx-auto flex h-14 max-w-7xl items-center px-4 sm:px-6 md:px-8">
          <Logo />
        </div>
      </header>
      <main className="flex-1">{children}</main>
    </div>
  );
}
