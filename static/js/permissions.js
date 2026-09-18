(() => {
  'use strict';

  const save = (key, value) => {
    try { localStorage.setItem(key, value); } catch {}
  };

  const publishLocation = (position) => {
    save('mtu-location-enabled', 'yes');
    window.dispatchEvent(new CustomEvent('mtu-location-ready', {
      detail: {
        lat: Number(position.coords.latitude.toFixed(2)),
        lng: Number(position.coords.longitude.toFixed(2)),
      },
    }));
  };

  const checkLocation = async () => {
    if (!navigator.geolocation || !window.isSecureContext) return;
    try {
      const permission = navigator.permissions
        ? await navigator.permissions.query({ name: 'geolocation' })
        : null;
      if (permission && permission.state !== 'granted') {
        save('mtu-location-enabled', permission.state === 'denied' ? 'no' : 'auto');
        return;
      }
      navigator.geolocation.getCurrentPosition(
        publishLocation,
        () => save('mtu-location-enabled', 'no'),
        { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 },
      );
    } catch {}
  };

  const resumeSound = async () => {
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (!AudioContext) return;
      const context = window.mtuAudioContext || (window.mtuAudioContext = new AudioContext());
      await context.resume();
      if (context.state === 'running') save('mtu-audio-enabled', 'yes');
    } catch {}
  };

  checkLocation();
  document.addEventListener('pointerdown', resumeSound, { once: true, passive: true });
  document.addEventListener('keydown', resumeSound, { once: true });
})();
