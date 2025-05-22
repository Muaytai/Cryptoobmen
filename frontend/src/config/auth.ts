export const authConfig = {
  google: {
    clientId: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || '',
    redirectUri: process.env.NEXT_PUBLIC_REDIRECT_URI || 'https://kripto-obmen.com/api/auth/callback/google',
  },
  yandex: {
    clientId: process.env.NEXT_PUBLIC_YANDEX_CLIENT_ID || '',
    redirectUri: process.env.NEXT_PUBLIC_REDIRECT_URI || 'https://kripto-obmen.com/api/auth/callback/yandex',
  }
}; 