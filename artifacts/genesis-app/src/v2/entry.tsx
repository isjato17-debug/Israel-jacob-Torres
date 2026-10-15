import { createElement } from 'react';
import { createRoot } from 'react-dom/client';
import GenesisNext from './GenesisNext';

const root = document.getElementById('root');
if (!root) throw new Error('Genesis preview root is missing');
createRoot(root).render(createElement(GenesisNext));
