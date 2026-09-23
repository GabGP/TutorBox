// Progress Tracking
// Saves to localStorage with optional server sync

const STORAGE_KEY = 'kuk_progress_v1';
const USER_KEY = 'kuk_current_user';

let _cache = null;

function loadFromStorage() {
  if (_cache) return _cache;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    _cache = raw ? JSON.parse(raw) : {};
  } catch {
    _cache = {};
  }
  return _cache;
}

function saveToStorage(data) {
  _cache = data;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch (e) {
    console.warn('Could not save progress to localStorage');
  }
}

/**
 * Get all progress data
 */
export function getProgress() {
  return loadFromStorage();
}

/**
 * Save a completed lesson with star count
 * @param {string} moduleId
 * @param {string} lessonId
 * @param {number} stars - 1 to 3
 */
export function saveLesson(moduleId, lessonId, stars) {
  const data = loadFromStorage();
  if (!data[moduleId]) data[moduleId] = {};

  const existing = data[moduleId][lessonId] || { stars: 0 };
  data[moduleId][lessonId] = {
    stars: Math.max(existing.stars, Math.min(3, stars)),
    completedAt: new Date().toISOString()
  };

  saveToStorage(data);
  return data[moduleId][lessonId];
}

/**
 * Get stars for a specific lesson
 */
export function getLessonStars(moduleId, lessonId) {
  const data = loadFromStorage();
  return data[moduleId]?.[lessonId]?.stars || 0;
}

/**
 * Get total stars across all lessons
 */
export function getTotalStars() {
  const data = loadFromStorage();
  let total = 0;
  for (const mod in data) {
    for (const lesson in data[mod]) {
      total += data[mod][lesson].stars || 0;
    }
  }
  return total;
}

/**
 * Get stars for a module (sum of all lessons in module)
 */
export function getModuleStars(moduleId) {
  const data = loadFromStorage();
  const mod = data[moduleId] || {};
  return Object.values(mod).reduce((sum, l) => sum + (l.stars || 0), 0);
}

/**
 * Get completion percentage for a module
 * @param {string} moduleId
 * @param {number} totalLessons - Total lessons in this module
 */
export function getModuleCompletion(moduleId, totalLessons) {
  const data = loadFromStorage();
  const mod = data[moduleId] || {};
  const completed = Object.values(mod).filter(l => l.stars > 0).length;
  return totalLessons > 0 ? Math.round((completed / totalLessons) * 100) : 0;
}

/**
 * Check if a lesson is unlocked
 * M1L1 always unlocked. Others require previous lesson complete.
 */
export function isLessonUnlocked(moduleId, lessonIndex, moduleIndex, lessonId) {
  if (moduleIndex === 0 && lessonIndex === 0) return true;

  const data = loadFromStorage();

  // First lesson of a module: need first lesson of previous module
  if (lessonIndex === 0 && moduleIndex > 0) {
    const prevModuleId = `m${moduleIndex}`;
    const prevMod = data[prevModuleId];
    if (!prevMod) return false;
    return Object.values(prevMod).some(l => l.stars > 0);
  }

  // Otherwise: need previous lesson in same module
  return false; // Will be checked by caller with actual lesson IDs
}

/**
 * Check if a module is unlocked
 */
export function isModuleUnlocked(moduleIndex) {
  if (moduleIndex === 0) return true;
  const prevId = `m${moduleIndex}`;
  const data = loadFromStorage();
  const prevMod = data[prevId] || {};
  return Object.values(prevMod).some(l => l.stars > 0);
}

/**
 * Check if a lesson is unlocked by lesson ID
 */
export function isLessonUnlockedById(moduleId, lessonId, allLessons) {
  const lessonIndex = allLessons.findIndex(l => l.id === lessonId);
  if (lessonIndex === 0) return true; // First lesson always unlocked if module is unlocked

  const data = loadFromStorage();
  const modData = data[moduleId] || {};
  const prevLessonId = allLessons[lessonIndex - 1]?.id;
  if (!prevLessonId) return false;
  return (modData[prevLessonId]?.stars || 0) > 0;
}

/**
 * Get current user from localStorage
 */
export function getCurrentUser() {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

/**
 * Save current user to localStorage
 */
export function setCurrentUser(user) {
  try {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  } catch (e) {
    console.warn('Could not save user');
  }
}

/**
 * Clear all progress (used for testing)
 */
export function clearProgress() {
  _cache = {};
  localStorage.removeItem(STORAGE_KEY);
}

