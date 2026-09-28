// @ts-check
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightLinksValidator from 'starlight-links-validator';
import { satteri } from '@astrojs/markdown-satteri';
import { brand } from './src/plugins/brand.mjs';

export default defineConfig({
  site: 'https://mathbeal.github.io',
  base: '/avenir-mcp',
  // The name avenir-mcp is set apart in the text of every page (see the plugin).
  markdown: { processor: satteri({ hastPlugins: [brand] }) },
  vite: {
    resolve: {
      // Real answers from avenir-mcp on the invented demo budget, written by `python -m docsgen`.
      alias: { '@snippets': fileURLToPath(new URL('./src/snippets', import.meta.url)) },
    },
  },
  integrations: [
    starlight({
      title: 'avenir-mcp',
      description: 'An unofficial MCP server for YNAB, built for agents.',
      logo: { src: './src/assets/logo.svg' },
      favicon: '/favicon.svg',
      // Fonts are served with the site: no request to a third-party font service.
      customCss: [
        '@fontsource-variable/source-sans-3',
        '@fontsource-variable/source-serif-4',
        './src/styles/theme.css',
      ],
      // The home pages get their own hero: install command and a conversation preview.
      components: {
        Hero: './src/components/Hero.astro',
        // Every page ends with the notice that avenir-mcp is unofficial.
        Footer: './src/components/Footer.astro',
      },
      defaultLocale: 'root',
      locales: {
        root: { label: 'English', lang: 'en' },
        fr: { label: 'Français', lang: 'fr' },
        es: { label: 'Español', lang: 'es' },
        de: { label: 'Deutsch', lang: 'de' },
        nl: { label: 'Nederlands', lang: 'nl' },
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
          translations: { fr: 'Premiers pas', es: 'Primeros pasos', de: 'Erste Schritte', nl: 'Aan de slag' },
          items: [
            'getting-started/install',
            'getting-started/first-conversation',
            'getting-started/features',
          ],
        },
        {
          label: 'Guides',
          translations: { fr: 'Guides', es: 'Guías', de: 'Anleitungen', nl: 'Handleidingen' },
          items: [{ autogenerate: { directory: 'guides' } }],
        },
        {
          label: 'Concepts',
          translations: { fr: 'Concepts', es: 'Conceptos', de: 'Konzepte', nl: 'Concepten' },
          items: [{ autogenerate: { directory: 'concepts' } }],
        },
        {
          label: 'Reference',
          translations: { fr: 'Référence', es: 'Referencia', de: 'Referenz', nl: 'Naslag' },
          items: [
            {
              label: 'Tools',
              translations: { fr: 'Outils', es: 'Herramientas', de: 'Tools', nl: 'Tools' },
              collapsed: true,
              items: [{ autogenerate: { directory: 'reference/tools' } }],
            },
            'reference/resources-and-prompts',
            'reference/configuration',
            'reference/errors',
            'reference/api-coverage',
          ],
        },
        {
          label: 'Project',
          translations: { fr: 'Projet', es: 'Proyecto', de: 'Projekt', nl: 'Project' },
          items: [{ autogenerate: { directory: 'project' } }],
        },
      ],
    }),
  ],
});
