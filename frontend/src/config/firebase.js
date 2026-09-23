import { initializeApp, getApps } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
  apiKey:
    process.env.REACT_APP_FIREBASE_API_KEY ||
    process.env.VITE_FIREBASE_API_KEY ||
    "AIzaSyA2tyGxHCq5guWy8w4UpAiU5ZzYEy3UsBM",
  authDomain:
    process.env.REACT_APP_FIREBASE_AUTH_DOMAIN ||
    process.env.VITE_FIREBASE_AUTH_DOMAIN ||
    "truthlens-6aa27.firebaseapp.com",
  projectId:
    process.env.REACT_APP_FIREBASE_PROJECT_ID ||
    process.env.VITE_FIREBASE_PROJECT_ID ||
    "truthlens-6aa27",
  storageBucket:
    process.env.REACT_APP_FIREBASE_STORAGE_BUCKET ||
    process.env.VITE_FIREBASE_STORAGE_BUCKET ||
    "truthlens-6aa27.firebasestorage.app",
  messagingSenderId:
    process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID ||
    process.env.VITE_FIREBASE_MESSAGING_SENDER_ID ||
    "221842927887",
  appId:
    process.env.REACT_APP_FIREBASE_APP_ID ||
    process.env.VITE_FIREBASE_APP_ID ||
    "1:221842927887:web:52a363a90729bcfcbe0e7a",
};

// Prevent duplicate initialization
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];

export const auth = getAuth(app);
export const db = getFirestore(app);
export const googleProvider = new GoogleAuthProvider();

export default app;
