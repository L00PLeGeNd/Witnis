import { TokenService } from "./auth";

export class CachingTokenService extends TokenService {
  issue(user: string): string {
    return `cache-${super.issue(user)}`;
  }
}
