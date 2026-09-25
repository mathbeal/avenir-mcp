/** Short texts of the home page components, in the site's three languages. */
const texts = {
  en: {
    eyebrow: 'Unofficial open-source MCP server for YNAB',
    install: 'claude mcp add avenir \\\n  --env YNAB_API_KEY=your-token \\\n  -- uvx avenir-mcp',
    worksWith: 'Works with',
    demoLabel: 'A conversation with Claude using Avenir',
    you: 'You',
    q1: 'Which category is overspent this month?',
    a1: 'Restaurants is <strong>22.50 over</strong>. Tennis still has 80.00 available — move 30 to cover it?',
    q2: 'Yes, do it.',
    preview: 'Preview',
    tennis: ['80.00', '50.00'],
    restaurants: ['120.00', '150.00'],
    confirm: 'Confirm',
    cancel: 'Cancel',
    undo: 'Journaled — undo with one sentence',
    stats: [
      ['17', 'tools, each doing a whole task'],
      ['100 %', 'line and branch coverage'],
      ['9 / 9', 'tasks passed by a real agent'],
      ['1–2', 'YNAB requests per call, most tools'],
    ],
    flow: [
      ['Preview', 'Avenir computes the exact change and shows it. Nothing is written yet.'],
      ['Confirm', 'You say yes in your client, or with a one-time code bound to that preview.'],
      ['Undo', 'Every applied change is journaled; undo restores it without overwriting later work.'],
    ],
    disclaimer:
      '<strong>Unofficial project.</strong> Avenir is not affiliated with, endorsed by or sponsored by YNAB. YNAB and You Need A Budget are registered trademarks of YNAB, used here only to say which service Avenir works with. Avenir uses YNAB’s public API with your own access token.',
  },
  fr: {
    eyebrow: 'Serveur MCP open source non officiel pour YNAB',
    install: 'claude mcp add avenir \\\n  --env YNAB_API_KEY=votre-jeton \\\n  -- uvx avenir-mcp',
    worksWith: 'Fonctionne avec',
    demoLabel: 'Une conversation avec Claude qui utilise Avenir',
    you: 'Vous',
    q1: 'Quelle catégorie est en dépassement ce mois-ci ?',
    a1: 'Restaurants dépasse de <strong>22,50</strong>. Il reste 80,00 dans Tennis — j’en déplace 30 pour couvrir ?',
    q2: 'Oui, vas-y.',
    preview: 'Aperçu',
    tennis: ['80,00', '50,00'],
    restaurants: ['120,00', '150,00'],
    confirm: 'Confirmer',
    cancel: 'Annuler',
    undo: 'Inscrit au journal — annulable en une phrase',
    stats: [
      ['17', 'outils, chacun mène une tâche entière'],
      ['100 %', 'de couverture des lignes et des branches'],
      ['9 / 9', 'tâches réussies par un vrai agent'],
      ['1–2', 'requêtes YNAB par appel, pour la plupart des outils'],
    ],
    flow: [
      ['Aperçu', 'Avenir calcule le changement exact et vous le montre. Rien n’est encore écrit.'],
      ['Confirmation', 'Vous dites oui dans votre client, ou avec un code à usage unique lié à cet aperçu.'],
      ['Annulation', 'Chaque changement appliqué est journalisé ; l’annulation le défait sans écraser le travail fait depuis.'],
    ],
    disclaimer:
      '<strong>Projet non officiel.</strong> Avenir n’est ni affilié à YNAB, ni approuvé, ni soutenu par YNAB. YNAB et You Need A Budget sont des marques déposées de YNAB, citées ici uniquement pour indiquer le service avec lequel Avenir fonctionne. Avenir utilise l’API publique de YNAB avec votre propre jeton d’accès.',
  },
  es: {
    eyebrow: 'Servidor MCP no oficial y de código abierto para YNAB',
    install: 'claude mcp add avenir \\\n  --env YNAB_API_KEY=su-token \\\n  -- uvx avenir-mcp',
    worksWith: 'Funciona con',
    demoLabel: 'Una conversación con Claude usando Avenir',
    you: 'Usted',
    q1: '¿Qué categoría se ha pasado este mes?',
    a1: 'Restaurants se ha pasado <strong>22,50</strong>. A Tennis le quedan 80,00 — ¿muevo 30 para cubrirlo?',
    q2: 'Sí, hazlo.',
    preview: 'Vista previa',
    tennis: ['80,00', '50,00'],
    restaurants: ['120,00', '150,00'],
    confirm: 'Confirmar',
    cancel: 'Cancelar',
    undo: 'Anotado en el diario — se deshace con una frase',
    stats: [
      ['17', 'herramientas, cada una hace una tarea completa'],
      ['100 %', 'de cobertura de líneas y ramas'],
      ['9 / 9', 'tareas superadas por un agente real'],
      ['1–2', 'peticiones a YNAB por llamada, en la mayoría'],
    ],
    flow: [
      ['Vista previa', 'Avenir calcula el cambio exacto y se lo muestra. Todavía no se escribe nada.'],
      ['Confirmación', 'Usted dice que sí en su cliente, o con un código de un solo uso ligado a esa vista previa.'],
      ['Deshacer', 'Cada cambio aplicado se anota en el diario; deshacer lo revierte sin sobrescribir el trabajo posterior.'],
    ],
    disclaimer:
      '<strong>Proyecto no oficial.</strong> Avenir no está afiliado a YNAB, ni respaldado ni patrocinado por YNAB. YNAB y You Need A Budget son marcas registradas de YNAB, citadas aquí solo para indicar con qué servicio funciona Avenir. Avenir usa la API pública de YNAB con su propio token de acceso.',
  },
} as const;

export type Lang = keyof typeof texts;

export function home(lang: string) {
  return texts[(lang in texts ? lang : 'en') as Lang];
}
