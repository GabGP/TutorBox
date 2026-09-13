import { useEffect, useState } from 'react';
import { DisplayView } from '../pages/display/DisplayView';
import { StudentView } from '../pages/student/StudentView';
import { TeacherView } from '../pages/teacher/TeacherView';
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

  let view = <StudentView />;
  if (pathname.includes('/maestro')) {
    view = <TeacherView />;
  } else if (pathname.includes('/pantalla')) {
    view = <DisplayView />;
  }

  return <ErrorBoundary>{view}</ErrorBoundary>;
}
