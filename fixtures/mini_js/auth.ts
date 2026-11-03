export class TokenService {
  issue(user: string): string {
    return `tok-${user}`;
  }
}

export function verifyToken(token: string): boolean {
  return token.startsWith("tok-");
}

export const refresh = async (token: string) => {
  return verifyToken(token) ? token : "";
};
