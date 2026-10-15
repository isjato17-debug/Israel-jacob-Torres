import { createElement } from 'react';
import { createRoot } from 'react-dom/client';
import GenesisNext from './GenesisNext';
import GuidedExperience from './GuidedExperience';
import OwnerGrowth from './OwnerGrowth';
import PartnerPortal from './PartnerPortal';
import PartnerOperator from './PartnerOperator';
import IdeaVault from './IdeaVault';

const root = document.getElementById('root');
if (!root) throw new Error('Genesis preview root is missing');
const path = window.location.pathname;
const page = /\/next\/ideas\/?$/.test(path) ? IdeaVault :
  /\/next\/owner\/partners\/?$/.test(path) ? PartnerOperator :
  /\/next\/partners\/?$/.test(path) ? PartnerPortal :
  /\/next\/owner\/?$/.test(path) ? OwnerGrowth :
  /\/next\/draft\/?$/.test(path) ? GenesisNext : GuidedExperience;
createRoot(root).render(createElement(page));
