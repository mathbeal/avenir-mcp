// SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
// SPDX-License-Identifier: MIT

/** Short texts of the home page components, in each of the site's languages. */
const texts = {
  en: {
    eyebrow: 'Unofficial open-source MCP server for YNAB',
    install: 'claude mcp add avenir-mcp \\\n  --env YNAB_API_KEY=your-token \\\n  -- uvx avenir-mcp',
    worksWith: 'Works with',
    demoLabel: 'A conversation with Claude using avenir-mcp',
    writeDemo:
      'Thirty seconds, one write: move_money previews moving 30 from Tennis to Restaurants — Tennis 80.00 → 50.00, Restaurants 120.00 → 150.00 — and changes nothing; once agreed, the move is applied and journaled; undo_operation then puts both amounts back.',
    you: 'You',
    q1: 'Which category is overspent this month?',
    a1: 'Restaurants is <strong>22.50 over</strong>. Tennis still has 80.00 available — move 30 to cover it?',
    q2: 'Yes, do it.',
    preview: 'Preview',
    names: ['Tennis', 'Restaurants'],
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
      ['Preview', 'avenir-mcp computes the exact change and shows it. Nothing is written yet.'],
      ['Confirm', 'You say yes in your client, or with a one-time code bound to that preview.'],
      ['Undo', 'Every applied change is journaled; undo restores it without overwriting later work.'],
    ],
    disclaimer:
      '<strong>Unofficial project.</strong> We are not affiliated, associated, or in any way officially connected with YNAB or any of its subsidiaries or affiliates. The official YNAB website can be found at <a href="https://www.ynab.com">https://www.ynab.com</a>. The names YNAB and You Need A Budget, as well as related names, tradenames, marks, trademarks, emblems, and images are registered trademarks of YNAB. avenir-mcp is provided as is, without warranty, and is not financial advice. <a href="/avenir-mcp/project/legal/">Legal notice</a> · <a href="/avenir-mcp/project/privacy/">Privacy</a>',
  },
  fr: {
    eyebrow: 'Serveur MCP open source non officiel pour YNAB',
    install: 'claude mcp add avenir-mcp \\\n  --env YNAB_API_KEY=votre-jeton \\\n  -- uvx avenir-mcp',
    worksWith: 'Fonctionne avec',
    demoLabel: 'Une conversation avec Claude qui utilise avenir-mcp',
    writeDemo:
      'Trente secondes, une écriture : move_money affiche l’aperçu d’un déplacement de 30 de Tennis vers Restaurants — Tennis 80,00 → 50,00, Restaurants 120,00 → 150,00 — et ne modifie rien ; une fois l’accord donné, le déplacement est appliqué et inscrit au journal ; undo_operation remet ensuite les deux montants comme avant.',
    you: 'Vous',
    q1: 'Quelle catégorie est en dépassement ce mois-ci ?',
    a1: 'Restaurants dépasse de <strong>22,50</strong>. Il reste 80,00 dans Escalade — j’en déplace 30 pour couvrir ?',
    q2: 'Oui, vas-y.',
    preview: 'Aperçu',
    names: ['Escalade', 'Restaurants'],
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
      ['Aperçu', 'avenir-mcp calcule le changement exact et vous le montre. Rien n’est encore écrit.'],
      ['Confirmation', 'Vous dites oui dans votre client, ou avec un code à usage unique lié à cet aperçu.'],
      ['Annulation', 'Chaque changement appliqué est journalisé ; l’annulation le défait sans écraser le travail fait depuis.'],
    ],
    disclaimer:
      '<strong>Projet non officiel.</strong> « We are not affiliated, associated, or in any way officially connected with YNAB or any of its subsidiaries or affiliates. The official YNAB website can be found at <a href="https://www.ynab.com">https://www.ynab.com</a>. The names YNAB and You Need A Budget, as well as related names, tradenames, marks, trademarks, emblems, and images are registered trademarks of YNAB. » Nous ne sommes ni affiliés, ni associés, ni liés officiellement de quelque manière que ce soit à YNAB ou à ses filiales et sociétés affiliées. Le site officiel de YNAB se trouve à l’adresse <a href="https://www.ynab.com">https://www.ynab.com</a>. Les noms YNAB et You Need A Budget, ainsi que les noms, dénominations commerciales, marques, emblèmes et images qui s’y rattachent, sont des marques déposées de YNAB. avenir-mcp est fourni tel quel, sans garantie, et n’est pas un conseil financier. <a href="/avenir-mcp/fr/project/legal/">Mentions légales</a> · <a href="/avenir-mcp/fr/project/privacy/">Confidentialité</a>',
  },
  es: {
    eyebrow: 'Servidor MCP no oficial y de código abierto para YNAB',
    install: 'claude mcp add avenir-mcp \\\n  --env YNAB_API_KEY=su-token \\\n  -- uvx avenir-mcp',
    worksWith: 'Funciona con',
    demoLabel: 'Una conversación con Claude usando avenir-mcp',
    writeDemo:
      'Treinta segundos, una escritura: move_money muestra una vista previa del traslado de 30 de Tennis a Restaurants — Tennis 80,00 → 50,00, Restaurants 120,00 → 150,00 — y no cambia nada; tras la aceptación, el traslado se aplica y queda anotado en el diario; después undo_operation devuelve ambos importes a como estaban.',
    you: 'Usted',
    q1: '¿Qué categoría se ha pasado este mes?',
    a1: 'Restaurantes se ha pasado <strong>22,50</strong>. A Pádel le quedan 80,00 — ¿muevo 30 para cubrirlo?',
    q2: 'Sí, hazlo.',
    preview: 'Vista previa',
    names: ['Pádel', 'Restaurantes'],
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
      ['Vista previa', 'avenir-mcp calcula el cambio exacto y se lo muestra. Todavía no se escribe nada.'],
      ['Confirmación', 'Usted dice que sí en su cliente, o con un código de un solo uso ligado a esa vista previa.'],
      ['Deshacer', 'Cada cambio aplicado se anota en el diario; deshacer lo revierte sin sobrescribir el trabajo posterior.'],
    ],
    disclaimer:
      '<strong>Proyecto no oficial.</strong> «We are not affiliated, associated, or in any way officially connected with YNAB or any of its subsidiaries or affiliates. The official YNAB website can be found at <a href="https://www.ynab.com">https://www.ynab.com</a>. The names YNAB and You Need A Budget, as well as related names, tradenames, marks, trademarks, emblems, and images are registered trademarks of YNAB.» No estamos afiliados, asociados ni conectados oficialmente de ninguna manera con YNAB ni con sus filiales o empresas afiliadas. El sitio web oficial de YNAB se encuentra en <a href="https://www.ynab.com">https://www.ynab.com</a>. Los nombres YNAB y You Need A Budget, así como los nombres, nombres comerciales, marcas, emblemas e imágenes relacionados, son marcas registradas de YNAB. avenir-mcp se ofrece tal cual, sin garantía, y no es asesoramiento financiero. <a href="/avenir-mcp/es/project/legal/">Aviso legal</a> · <a href="/avenir-mcp/es/project/privacy/">Privacidad</a>',
  },
  de: {
    eyebrow: 'Inoffizieller Open-Source-MCP-Server für YNAB',
    install: 'claude mcp add avenir-mcp \\\n  --env YNAB_API_KEY=ihr-token \\\n  -- uvx avenir-mcp',
    worksWith: 'Funktioniert mit',
    demoLabel: 'Ein Gespräch mit Claude über avenir-mcp',
    writeDemo:
      'Dreißig Sekunden, eine Änderung: move_money zeigt eine Vorschau, wie 30 von Tennis zu Restaurants umgebucht werden — Tennis 80,00 → 50,00, Restaurants 120,00 → 150,00 — und ändert nichts; nach der Zustimmung wird die Umbuchung angewendet und im Journal erfasst; danach setzt undo_operation beide Beträge zurück.',
    you: 'Sie',
    q1: 'Welche Kategorie ist diesen Monat überzogen?',
    a1: 'Restaurants liegt <strong>22,50 darüber</strong>. Tennis hat noch 80,00 verfügbar – 30 davon umbuchen, um es auszugleichen?',
    q2: 'Ja, mach das.',
    preview: 'Vorschau',
    names: ['Tennis', 'Restaurants'],
    tennis: ['80,00', '50,00'],
    restaurants: ['120,00', '150,00'],
    confirm: 'Bestätigen',
    cancel: 'Abbrechen',
    undo: 'Im Journal – mit einem Satz rückgängig zu machen',
    stats: [
      ['17', 'Tools, jedes erledigt eine ganze Aufgabe'],
      ['100 %', 'Zeilen- und Zweigabdeckung'],
      ['9 / 9', 'Aufgaben von einem echten Agenten bestanden'],
      ['1–2', 'YNAB-Anfragen pro Aufruf, bei den meisten Tools'],
    ],
    flow: [
      ['Vorschau', 'avenir-mcp berechnet die genaue Änderung und zeigt sie. Noch wird nichts geschrieben.'],
      ['Bestätigung', 'Sie sagen Ja in Ihrem Client oder mit einem Einmalcode, der an diese Vorschau gebunden ist.'],
      ['Rückgängig', 'Jede angewendete Änderung wird im Journal erfasst; das Rückgängigmachen stellt sie wieder her, ohne spätere Arbeit zu überschreiben.'],
    ],
    disclaimer:
      '<strong>Inoffizielles Projekt.</strong> „We are not affiliated, associated, or in any way officially connected with YNAB or any of its subsidiaries or affiliates. The official YNAB website can be found at <a href="https://www.ynab.com">https://www.ynab.com</a>. The names YNAB and You Need A Budget, as well as related names, tradenames, marks, trademarks, emblems, and images are registered trademarks of YNAB.“ Wir sind mit YNAB oder einer seiner Tochtergesellschaften oder verbundenen Unternehmen weder verbunden noch assoziiert noch in irgendeiner Weise offiziell verknüpft. Die offizielle Website von YNAB finden Sie unter <a href="https://www.ynab.com">https://www.ynab.com</a>. Die Namen YNAB und You Need A Budget sowie zugehörige Namen, Handelsnamen, Zeichen, Marken, Embleme und Bilder sind eingetragene Marken von YNAB. avenir-mcp wird ohne Gewähr bereitgestellt und ist keine Finanzberatung. <a href="/avenir-mcp/de/project/legal/">Rechtliche Hinweise</a> · <a href="/avenir-mcp/de/project/privacy/">Datenschutz</a>',
  },
  nl: {
    eyebrow: 'Onofficiële opensource-MCP-server voor YNAB',
    install: 'claude mcp add avenir-mcp \\\n  --env YNAB_API_KEY=jouw-token \\\n  -- uvx avenir-mcp',
    worksWith: 'Werkt met',
    demoLabel: 'Een gesprek met Claude via avenir-mcp',
    writeDemo:
      'Dertig seconden, één schrijfactie: move_money toont een voorbeeld van het overhevelen van 30 van Tennis naar Restaurants — Tennis 80,00 → 50,00, Restaurants 120,00 → 150,00 — en verandert niets; na akkoord wordt de overheveling toegepast en in het journaal gezet; daarna zet undo_operation beide bedragen terug.',
    you: 'Jij',
    q1: 'Welke categorie zit deze maand over budget?',
    a1: 'Restaurants zit <strong>22,50 over budget</strong>. Tennis heeft nog 80,00 beschikbaar – 30 overhevelen om het te dekken?',
    q2: 'Ja, doe maar.',
    preview: 'Voorbeeld',
    names: ['Tennis', 'Restaurants'],
    tennis: ['80,00', '50,00'],
    restaurants: ['120,00', '150,00'],
    confirm: 'Bevestigen',
    cancel: 'Annuleren',
    undo: 'In het journaal – met één zin ongedaan te maken',
    stats: [
      ['17', 'tools, elk voor een hele taak'],
      ['100 %', 'dekking van regels en vertakkingen'],
      ['9 / 9', 'taken gehaald door een echte agent'],
      ['1–2', 'YNAB-verzoeken per aanroep, bij de meeste tools'],
    ],
    flow: [
      ['Voorbeeld', 'avenir-mcp berekent de exacte wijziging en laat die zien. Er wordt nog niets geschreven.'],
      ['Bevestiging', 'Je zegt ja in je client, of met een eenmalige code die aan dat voorbeeld gekoppeld is.'],
      ['Ongedaan maken', 'Elke toegepaste wijziging staat in het journaal; ongedaan maken herstelt haar zonder later werk te overschrijven.'],
    ],
    disclaimer:
      '<strong>Onofficieel project.</strong> “We are not affiliated, associated, or in any way officially connected with YNAB or any of its subsidiaries or affiliates. The official YNAB website can be found at <a href="https://www.ynab.com">https://www.ynab.com</a>. The names YNAB and You Need A Budget, as well as related names, tradenames, marks, trademarks, emblems, and images are registered trademarks of YNAB.” We zijn op geen enkele manier verbonden, geassocieerd of officieel gelieerd aan YNAB of een van zijn dochterondernemingen of gelieerde bedrijven. De officiële website van YNAB vind je op <a href="https://www.ynab.com">https://www.ynab.com</a>. De namen YNAB en You Need A Budget, evenals verwante namen, handelsnamen, merken, emblemen en afbeeldingen, zijn geregistreerde handelsmerken van YNAB. avenir-mcp wordt geleverd zoals het is, zonder garantie, en is geen financieel advies. <a href="/avenir-mcp/nl/project/legal/">Juridische informatie</a> · <a href="/avenir-mcp/nl/project/privacy/">Privacy</a>',
  },
} as const;

export type Lang = keyof typeof texts;

/**
 * Sets the name avenir-mcp apart, as the Markdown pages do (src/plugins/brand.mjs).
 * Only a mention in text: the name inside a path such as /avenir-mcp/ stays as it is.
 */
export function branded(html: string): string {
  return html.replace(/(?<![\w/-])avenir-mcp(?![\w/-])/g, '<span class="brand">avenir-mcp</span>');
}

export function home(lang: string) {
  return texts[(lang in texts ? lang : 'en') as Lang];
}
