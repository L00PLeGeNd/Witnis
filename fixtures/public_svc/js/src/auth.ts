export class TokenGateway {
  issue(user: string): string {
    return `tok-${user}`;
  }

  verify(token: string): boolean {
    return token.startsWith("tok-");
  }
}

export function requireToken(token: string): boolean {
  const gw = new TokenGateway();
  return gw.verify(token);
}
