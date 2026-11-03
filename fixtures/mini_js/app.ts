import { TokenService, verifyToken } from "./auth";

export function bootstrap(user: string): string {
  const svc = new TokenService();
  const token = svc.issue(user);
  return verifyToken(token) ? token : "";
}
