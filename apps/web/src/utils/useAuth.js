import { useCallback } from "react";
import { signIn, signOut } from "@auth/create/react";

function useAuth() {
  const callbackUrl =
    typeof window !== "undefined"
      ? new URLSearchParams(window.location.search).get("callbackUrl")
      : null;

  const signInWithCredentials = useCallback(
    (options) => {
      return signIn("credentials-signin", {
        ...options,
        callbackUrl: callbackUrl ?? options.callbackUrl,
      });
    },
    [callbackUrl],
  );

  const signUpWithCredentials = useCallback(
    (options) => {
      return signIn("credentials-signup", {
        ...options,
        callbackUrl: callbackUrl ?? options.callbackUrl,
      });
    },
    [callbackUrl],
  );

  return {
    signInWithCredentials,
    signUpWithCredentials,
    signOut,
  };
}

export default useAuth;
