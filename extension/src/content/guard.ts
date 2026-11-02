declare global {
  interface Window {
    __linkedinWorkbenchInjected?: boolean;
  }
}

export function shouldInject(win: Window): boolean {
  return !win.__linkedinWorkbenchInjected;
}
