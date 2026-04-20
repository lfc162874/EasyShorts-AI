import { computed, ref } from "vue";
import { defineStore } from "pinia";

import { getCurrentUser, login, logout } from "@/api/modules/auth";
import type { LoginPayload, UserProfile } from "@/types/system";

const TOKEN_KEY = "easyshorts-access-token";
const USER_KEY = "easyshorts-user";

const readStoredUser = (): UserProfile | null => {
  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as UserProfile;
  } catch {
    return null;
  }
};

export const useAuthStore = defineStore("auth", () => {
  const token = ref(window.localStorage.getItem(TOKEN_KEY) ?? "");
  const user = ref<UserProfile | null>(readStoredUser());

  const isLoggedIn = computed(() => Boolean(window.localStorage.getItem(TOKEN_KEY)));
  const permissions = computed(() => user.value?.permissions ?? []);
  const isSuperAdmin = computed(() => Boolean(user.value?.is_superuser));

  const setToken = (value: string) => {
    token.value = value;
    if (value) {
      window.localStorage.setItem(TOKEN_KEY, value);
      return;
    }
    window.localStorage.removeItem(TOKEN_KEY);
  };

  const setUser = (value: UserProfile | null) => {
    user.value = value;
    if (value) {
      window.localStorage.setItem(USER_KEY, JSON.stringify(value));
      return;
    }
    window.localStorage.removeItem(USER_KEY);
  };

  const loginAction = async (payload: LoginPayload) => {
    const response = await login(payload);
    setToken(response.data.access_token);
    setUser(response.data.user);
    return response.data;
  };

  const fetchCurrentUser = async () => {
    const storedToken = window.localStorage.getItem(TOKEN_KEY) ?? "";
    if (!storedToken) {
      setToken("");
      setUser(null);
      return null;
    }
    if (storedToken !== token.value) {
      token.value = storedToken;
    }
    const response = await getCurrentUser();
    setUser(response.data);
    return response.data;
  };

  const logoutAction = async () => {
    try {
      if (token.value) {
        await logout();
      }
    } finally {
      setToken("");
      setUser(null);
    }
  };

  return {
    token,
    user,
    permissions,
    isLoggedIn,
    isSuperAdmin,
    loginAction,
    fetchCurrentUser,
    logoutAction,
    setToken,
    setUser,
  };
});
