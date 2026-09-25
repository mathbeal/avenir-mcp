// @ts-check
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightLinksValidator from 'starlight-links-validator';

export default defineConfig({
  site: 'https://mathbeal.github.io',
  base: '/avenir-mcp',
  vite: {
    resolve: {
      // Real answers from Avenir on the invented demo budget, written by `python -m docsgen`.
      alias: { '@snippets': fileURLToPath(new URL('./src/snippets', import.meta.url)) },
    },
  },
  integrations: [
    starlight({
      title: 'Avenir',
      description: 'An MCP server for YNAB, built for agents.',
      defaultLocale: 'root',
      locales: {
        root: { label: 'English', lang: 'en' },
        fr: { label: 'Français', lang: 'fr' },
        es: { label: 'Español', lang: 'es' },
      },
      social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/mathbeal/avenir-mcp' }],
      editLink: { baseUrl: 'https://github.com/mathbeal/avenir-mcp/edit/main/docs/' },
      lastUpdated: true,
      // A broken internal link, in any language, fails the build. The generated pages
      // (tool reference, security) exist in English only, on purpose: they are copied from
      // the code and SECURITY.md, and translations would drift. Other languages link to
      // Starlight's fallback, which shows them with a "not translated" notice.
      plugins: [starlightLinksValidator({ errorOnFallbackPages: false })],
      sidebar: [
        {
          label: 'Getting started',
          translations: { fr: 'Premiers pas', es: 'Primeros pasos' },
          items: ['getting-started/install', 'getting-started/first-conversation'],
        },
        {
          label: 'Use cases',
          translations: { fr: "Cas d'usage", es: 'Casos de uso' },
          items: [{ autogenerate: { directory: 'use-cases' } }],
        },
        {
          label: 'Concepts',
          translations: { fr: 'Concepts', es: 'Conceptos' },
          items: [{ autogenerate: { directory: 'concepts' } }],
        },
        {
          label: 'Reference',
          translations: { fr: 'Référence', es: 'Referencia' },
          items: [{ autogenerate: { directory: 'reference' } }],
        },
        {
          label: 'Project',
          translations: { fr: 'Projet', es: 'Proyecto' },
          items: ['security', 'evaluation', 'troubleshooting'],
        },
      ],
    }),
  ],
});
