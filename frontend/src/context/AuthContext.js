import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
  onAuthStateChanged,
  updateProfile,
  sendPasswordResetEmail,
} from 'firebase/auth';
import {
  doc,
  getDoc,
  setDoc,
  serverTimestamp,
  onSnapshot,
} from 'firebase/firestore';
import { auth, db, googleProvider } from '../config/firebase';

const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

// Convert raw Firebase error codes into friendly user messages
export function formatAuthError(error) {
  if (!error) return '';
  const code = error.code || '';
  switch (code) {
    case 'auth/email-already-in-use':
      return 'An account with this email address already exists.';
    case 'auth/invalid-email':
      return 'Please enter a valid email address.';
    case 'auth/user-not-found':
    case 'auth/wrong-password':
    case 'auth/invalid-credential':
      return 'Invalid email or password.';
    case 'auth/weak-password':
      return 'Password must be at least 6 characters long.';
    case 'auth/popup-closed-by-user':
      return 'Google sign-in was cancelled.';
    case 'auth/account-exists-with-different-credential':
      return 'An account already exists with the same email address using a different sign-in method.';
    case 'permission-denied':
      return "You don't have permission to perform this action.";
    case 'auth/network-request-failed':
      return 'Network connection error. Please check your internet connection.';
    default:
      return error.message || 'An unexpected authentication error occurred. Please try again.';
  }
}

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Monitor auth state changes
  useEffect(() => {
    let unsubscribeProfile = null;

    const unsubscribeAuth = onAuthStateChanged(auth, async (user) => {
      setCurrentUser(user);
      if (user) {
        // Real-time listener for Firestore user profile
        const userRef = doc(db, 'users', user.uid);
        unsubscribeProfile = onSnapshot(
          userRef,
          (docSnap) => {
            if (docSnap.exists()) {
              setUserProfile(docSnap.data());
            } else {
              setUserProfile(null);
            }
            setLoading(false);
          },
          () => {
            setLoading(false);
          }
        );
      } else {
        setUserProfile(null);
        if (unsubscribeProfile) unsubscribeProfile();
        setLoading(false);
      }
    });

    return () => {
      unsubscribeAuth();
      if (unsubscribeProfile) unsubscribeProfile();
    };
  }, []);

  // Email/Password Signup
  const signup = async (email, password, fullName) => {
    setError(null);
    try {
      const res = await createUserWithEmailAndPassword(auth, email, password);
      // Update Firebase auth profile
      if (fullName) {
        await updateProfile(res.user, { displayName: fullName });
      }

      // Provision user document in Firestore (never store password)
      const userRef = doc(db, 'users', res.user.uid);
      const profileData = {
        uid: res.user.uid,
        name: fullName || res.user.email?.split('@')[0] || 'Investigator',
        email: res.user.email,
        photoURL: null,
        provider: 'password',
        createdAt: serverTimestamp(),
        updatedAt: serverTimestamp(),
      };
      await setDoc(userRef, profileData);
      setUserProfile(profileData);
      return res.user;
    } catch (err) {
      const friendly = formatAuthError(err);
      setError(friendly);
      throw new Error(friendly);
    }
  };

  // Email/Password Login
  const login = async (email, password) => {
    setError(null);
    try {
      const res = await signInWithEmailAndPassword(auth, email, password);
      return res.user;
    } catch (err) {
      const friendly = formatAuthError(err);
      setError(friendly);
      throw new Error(friendly);
    }
  };

  // Google Sign-In
  const googleLogin = async () => {
    setError(null);
    try {
      const res = await signInWithPopup(auth, googleProvider);
      const user = res.user;

      // Check if Firestore user document exists
      const userRef = doc(db, 'users', user.uid);
      const userSnap = await getDoc(userRef);

      if (!userSnap.exists()) {
        const newProfile = {
          uid: user.uid,
          name: user.displayName || user.email?.split('@')[0] || 'Investigator',
          email: user.email,
          photoURL: user.photoURL || null,
          provider: 'google',
          createdAt: serverTimestamp(),
          updatedAt: serverTimestamp(),
        };
        await setDoc(userRef, newProfile);
        setUserProfile(newProfile);
      } else {
        await setDoc(
          userRef,
          {
            name: user.displayName || userSnap.data()?.name,
            email: user.email,
            photoURL: user.photoURL || userSnap.data()?.photoURL || null,
            updatedAt: serverTimestamp(),
          },
          { merge: true }
        );
      }
      return user;
    } catch (err) {
      const friendly = formatAuthError(err);
      setError(friendly);
      throw new Error(friendly);
    }
  };

  // Logout
  const logout = async () => {
    setError(null);
    try {
      await signOut(auth);
      setCurrentUser(null);
      setUserProfile(null);
    } catch (err) {
      const friendly = formatAuthError(err);
      setError(friendly);
      throw new Error(friendly);
    }
  };

  // Update Profile Name / Photo
  const updateUserProfileData = async ({ name, photoURL }) => {
    if (!currentUser) return;
    setError(null);
    try {
      const updates = {};
      if (name !== undefined) updates.displayName = name;
      if (photoURL !== undefined) updates.photoURL = photoURL;
      
      await updateProfile(currentUser, updates);

      const userRef = doc(db, 'users', currentUser.uid);
      const docUpdates = { updatedAt: serverTimestamp() };
      if (name !== undefined) docUpdates.name = name;
      if (photoURL !== undefined) docUpdates.photoURL = photoURL;
      
      await setDoc(userRef, docUpdates, { merge: true });
    } catch (err) {
      const friendly = formatAuthError(err);
      setError(friendly);
      throw new Error(friendly);
    }
  };

  // Password Reset
  const resetPassword = async (email) => {
    setError(null);
    try {
      await sendPasswordResetEmail(auth, email);
    } catch (err) {
      const friendly = formatAuthError(err);
      setError(friendly);
      throw new Error(friendly);
    }
  };

  const value = {
    user: currentUser,
    userProfile,
    loading,
    error,
    setError,
    signup,
    login,
    googleLogin,
    logout,
    updateUserProfileData,
    resetPassword,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
