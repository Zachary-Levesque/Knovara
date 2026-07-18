const STORAGE_KEY = "knovara.selectedCollection";
const PROJECT_KEY = "knovara.selectedProjectId";
const DEFAULT_COLLECTION = "seets";

export function getSelectedCollection(): string {
  if (typeof window === "undefined") {
    return DEFAULT_COLLECTION;
  }

  return window.localStorage.getItem(STORAGE_KEY) || DEFAULT_COLLECTION;
}

export function setSelectedCollection(collectionName: string) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(STORAGE_KEY, collectionName || DEFAULT_COLLECTION);
}

export function getSelectedProjectId(): number | null {
  if (typeof window === "undefined") {
    return null;
  }

  const value = window.localStorage.getItem(PROJECT_KEY);
  return value ? Number(value) : null;
}

export function setSelectedProjectId(projectId: number | null) {
  if (typeof window === "undefined") {
    return;
  }

  if (projectId === null) {
    window.localStorage.removeItem(PROJECT_KEY);
    return;
  }

  window.localStorage.setItem(PROJECT_KEY, String(projectId));
}
