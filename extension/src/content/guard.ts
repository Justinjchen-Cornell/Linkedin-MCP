export function shouldInject(win: { __linkedinWorkbenchInjected?: boolean }): boolean {
  return !win.__linkedinWorkbenchInjected;
}
