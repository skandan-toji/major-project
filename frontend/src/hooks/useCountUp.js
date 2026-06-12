import { useState, useEffect, useRef } from 'react';
import { useInView } from 'framer-motion';

export default function useCountUp(target, duration = 1500, decimals = 0) {
  const [value, setValue] = useState(0);
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, amount: 0.3 });
  const started = useRef(false);

  useEffect(() => {
    if (!inView || started.current || !target) return;
    started.current = true;
    const t0 = performance.now();
    const step = (now) => {
      const p = Math.min((now - t0) / duration, 1);
      const ease = 1 - Math.pow(1 - p, 3);
      setValue(+(ease * target).toFixed(decimals));
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [inView, target, duration, decimals]);

  return [ref, value];
}
