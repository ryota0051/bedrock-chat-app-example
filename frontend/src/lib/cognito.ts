import {
  CognitoUserPool,
  CognitoUser,
  AuthenticationDetails,
  CognitoUserSession,
} from 'amazon-cognito-identity-js';

let userPool: CognitoUserPool | null = null;

function getUserPool(): CognitoUserPool {
  if (!userPool) {
    const poolData = {
      UserPoolId: process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID || '',
      ClientId: process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID || '',
    };

    if (!poolData.UserPoolId || !poolData.ClientId) {
      throw new Error('Cognito configuration is missing. Please check environment variables.');
    }

    userPool = new CognitoUserPool(poolData);
  }
  return userPool;
}

export interface LoginResult {
  success: boolean;
  idToken?: string;
  username?: string;
  error?: string;
}

export async function login(username: string, password: string): Promise<LoginResult> {
  return new Promise((resolve) => {
    try {
      const pool = getUserPool();
      const authenticationDetails = new AuthenticationDetails({
        Username: username,
        Password: password,
      });

      const cognitoUser = new CognitoUser({
        Username: username,
        Pool: pool,
      });

      cognitoUser.authenticateUser(authenticationDetails, {
        onSuccess: (session: CognitoUserSession) => {
          const idToken = session.getIdToken().getJwtToken();
          resolve({
            success: true,
            idToken,
            username,
          });
        },
        onFailure: (err) => {
          resolve({
            success: false,
            error: err.message || 'ログインに失敗しました',
          });
        },
      });
    } catch (error) {
      resolve({
        success: false,
        error: error instanceof Error ? error.message : 'ログインに失敗しました',
      });
    }
  });
}

export function logout(): void {
  try {
    const pool = getUserPool();
    const currentUser = pool.getCurrentUser();
    if (currentUser) {
      currentUser.signOut();
    }
  } catch {
    // Ignore errors during logout
  }
}

export function getCurrentSession(): Promise<CognitoUserSession | null> {
  return new Promise((resolve) => {
    try {
      const pool = getUserPool();
      const currentUser = pool.getCurrentUser();
      if (!currentUser) {
        resolve(null);
        return;
      }

      currentUser.getSession((err: Error | null, session: CognitoUserSession | null) => {
        if (err || !session || !session.isValid()) {
          resolve(null);
          return;
        }
        resolve(session);
      });
    } catch {
      resolve(null);
    }
  });
}

export async function getIdToken(): Promise<string | null> {
  const session = await getCurrentSession();
  if (!session) return null;
  return session.getIdToken().getJwtToken();
}

export function getCurrentUsername(): string | null {
  try {
    const pool = getUserPool();
    const currentUser = pool.getCurrentUser();
    return currentUser?.getUsername() || null;
  } catch {
    return null;
  }
}
