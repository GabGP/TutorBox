import React, { useEffect, useState } from 'react';

/** "Actualizado hace N s", counting up each second; it only re-renders this line. */
export const SampleAge: React.FC<{ sampledAt: string }> = ({ sampledAt }) => {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);

  const seconds = Math.max(0, Math.round((now - Date.parse(sampledAt)) / 1000));
  return <span>Actualizado hace {seconds} s</span>;
};
