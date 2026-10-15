import { createElement } from 'react';
import { createRoot } from 'react-dom/client';
import GenesisNext from './GenesisNext';
import GuidedExperience from './GuidedExperience';

const root = document.getElementById('root');
if (!root) throw new Error('Genesis preview root is missing');
const page = /\/next\/draft\/?$/.test(window.location.pathname) ? GenesisNext : GuidedExperience;
createRoot(root).render(createElement(page));
