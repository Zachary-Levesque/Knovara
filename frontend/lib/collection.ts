const STORAGE_KEY = "knovara.selectedCollection";
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
