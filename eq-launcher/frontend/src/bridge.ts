export interface Status {
  channel: string;
  client_dir: string;
  phase: string;
  message: string;
  supported: boolean;
  configured: boolean;
  busy: boolean;
  release: number;
  installed_release: number;
  recovery_required: boolean;
  files: { path: string; state: "current" | "changed" | "missing" }[];
  remove: string[];
  events: { time: string; message: string }[];
  can_check: boolean;
  can_update: boolean;
  can_recover: boolean;
  can_play: boolean;
}
export interface NativeAPI {
  GetStatus(): Promise<Status>;
  ChooseClient(): Promise<void>;
  CheckForUpdates(): Promise<void>;
  Update(): Promise<void>;
  Recover(): Promise<void>;
  Cancel(): Promise<void>;
  Play(): Promise<void>;
  OpenGuide(): Promise<void>;
}
declare global {
  interface Window {
    go?: { main?: { App?: NativeAPI } };
  }
}
export const native = () => window.go?.main?.App;
export const initial: Status = {
  channel: "Development preview",
  client_dir: "",
  phase: "choose",
  message: "Choose your EverQuest folder to begin.",
  supported: false,
  configured: false,
  busy: false,
  release: 0,
  installed_release: 0,
  recovery_required: false,
  files: [],
  remove: [],
  events: [],
  can_check: false,
  can_update: false,
  can_recover: false,
  can_play: false,
};
export async function snapshot(): Promise<Status> {
  const api = native();
  if (api) return api.GetStatus();
  return {
    ...initial,
    phase: "browser_preview",
    message: "Open the desktop launcher to choose your client folder.",
  };
}
export async function invoke(
  action: Exclude<keyof NativeAPI, "GetStatus">,
): Promise<void> {
  const api = native();
  if (!api)
    throw new Error("This action is available in the desktop launcher.");
  await api[action]();
}
