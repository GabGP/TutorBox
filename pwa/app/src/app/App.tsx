import { useEffect, useState } from 'react';
import { DisplayView } from '../pages/display/DisplayView';
import { StudentView } from '../pages/student/StudentView';
import { TeacherView } from '../pages/teacher/TeacherView';
import { getPortal } from '../shared/routing/session';
import { ErrorBoundary } from './ErrorBoundary';

/**
 * Root Application router component.
 * Selects and renders the appropriate appliance mode view (Teacher, HDMI Display, or Student)
 * based on the current window location pathname, wrapped in an ErrorBoundary.
 *
 * @returns {JSX.Element} The active view corresponding to the current URL route.
 */
export function App() {
  const [pathname, setPathname] = useState(() => window.location.pathname);

  useEffect(() => {
    const handlePopState = () => setPathname(window.location.pathname);
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const portal = getPortal(pathname);
  let view = <StudentView />;
  if (portal === 'teacher') {
    view = <TeacherView />;
  } else if (portal === 'display') {
    view = <DisplayView />;
  }

  return <ErrorBoundary>{view}</ErrorBoundary>;
}
