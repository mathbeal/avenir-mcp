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
      'One conversation, in thirty seconds. Asked how the month is going and where the room is, the agent calls four read-only tools at the same time: Month summary, Every category, Budget vs spent and Three months. It answers that Restaurants is the only category over budget: 166.50 spent of 144.00 available (120.00 budgeted + 24.00 left from earlier months), 138.8 %, available −22.50; that its spending rose 113.70 → 119.90 → 166.50 over three months; and that 80.00 is left in Tennis and 411.90 in Groceries. It offers to cover the 22.50 from Tennis, which has nothing spent yet. The user answers “Cover it from Tennis.”, and move_money shows a preview that changes nothing: Tennis budgeted 80.00 → 57.50, Restaurants budgeted 120.00 → 142.50, available −22.50 → 0.00, exactly on budget, with a Cancel button, a Confirm button, and the reminder that nothing changes until you confirm and that any change can be undone.',
    tour: 'A 20-second tour of avenir-mcp: a question about an overspent category, four tools reading the plan at once, the exact fix previewed, confirmed and undoable, and the command that installs avenir-mcp.',
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
      'Une conversation, en trente secondes. Lorsqu’on lui demande comment se passe le mois et où il reste de la marge, l’agent appelle simultanément quatre outils en lecture seule : Month summary, Every category, Budget vs spent et Three months. Il répond que la catégorie Restaurants est la seule à dépasser le budget : 166,50 dépensés sur 144,00 disponibles (120,00 prévus au budget + 24,00 restants des mois précédents), soit 138,8 %, disponible −22,50 ; que ses dépenses sont passées de 113,70 à 119,90 puis à 166,50 sur trois mois ; et qu’il reste 80,00 dans la catégorie Tennis et 411,90 dans la catégorie Groceries. Il propose de prélever les 22,50 sur Tennis, qui n’a encore fait l’objet d’aucune dépense. L’utilisateur répond « Cover it from Tennis. », et la fonction move_money affiche un aperçu qui ne modifie rien : budget de Tennis 80,00 → 57,50, budget de Restaurants 120,00 → 142,50, disponible −22,50 → 0,00, ce qui correspond exactement au budget, avec un bouton Cancel, un bouton Confirm et un rappel indiquant que rien ne change tant que vous n’avez pas confirmé et que toute modification peut être annulée.',
    tour: 'Une présentation de 20 secondes d’avenir-mcp : une question sur une catégorie en dépassement, quatre outils qui lisent le plan en même temps, la correction exacte en aperçu, confirmée et annulable, puis la commande qui installe avenir-mcp.',
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
      'Una conversación de treinta segundos. Al preguntarle cómo va el mes y dónde queda margen, el agente llama simultáneamente a cuatro herramientas de solo lectura: Month summary, Every category, Budget vs spent y Three months. Responde que Restaurants es la única categoría que supera el presupuesto: 166,50 gastados de los 144,00 disponibles (120,00 presupuestados + 24,00 restantes de meses anteriores), un 138,8 %, disponible −22,50; que su gasto ha aumentado de 113,70 a 119,90 y a 166,50 a lo largo de tres meses; y que quedan 80,00 en Tennis y 411,90 en Groceries. Propone cubrir los 22,50 con cargo a Tennis, donde aún no se ha gastado nada. El usuario responde «Cover it from Tennis.», y move_money muestra una vista previa en la que no cambia nada: presupuesto de Tennis 80,00 → 57,50, presupuesto de Restaurants 120,00 → 142,50, disponible −22,50 → 0,00, exactamente dentro del presupuesto, con un botón Cancel, un botón Confirm y el recordatorio de que nada cambia hasta que usted lo confirme y de que cualquier cambio se puede deshacer.',
    tour: 'Un recorrido de 20 segundos por avenir-mcp: una pregunta sobre una categoría excedida, cuatro herramientas que leen el plan a la vez, la solución exacta en vista previa, confirmada y que se puede deshacer, y el comando que instala avenir-mcp.',
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
      'Ein Gespräch in dreißig Sekunden. Auf die Frage, wie der Monat verläuft und wo noch Spielraum besteht, ruft der Agent gleichzeitig vier schreibgeschützte Tools auf: Month summary, Every category, Budget vs spent und Three months. Er antwortet, dass Restaurants die einzige Kategorie ist, die das Budget überschreitet: 166,50 ausgegeben von 144,00 verfügbar (120,00 budgetiert + 24,00 übrig aus früheren Monaten), 138,8 %, verfügbar −22,50; dass die Ausgaben dieser Kategorie über drei Monate hinweg von 113,70 → 119,90 → 166,50 gestiegen sind; und dass in der Kategorie Tennis noch 80,00 und in der Kategorie Groceries noch 411,90 übrig sind. Er schlägt vor, die 22,50 aus der Kategorie Tennis zu decken, in der noch keine Ausgaben getätigt wurden. Der Nutzer antwortet „Cover it from Tennis.“, und move_money zeigt eine Vorschau an, die nichts ändert: Budget der Kategorie Tennis 80,00 → 57,50, Budget der Kategorie Restaurants 120,00 → 142,50, verfügbar −22,50 → 0,00, genau im Rahmen des Budgets, mit einer Schaltfläche Cancel, einer Schaltfläche Confirm und dem Hinweis, dass sich nichts ändert, bis Sie bestätigen, und dass jede Änderung rückgängig gemacht werden kann.',
    tour: 'Ein 20-sekündiger Rundgang durch avenir-mcp: eine Frage zu einer überzogenen Kategorie, vier Tools, die den Plan gleichzeitig lesen, die genaue Korrektur in der Vorschau, bestätigt und rückgängig machbar, sowie der Befehl zur Installation von avenir-mcp.',
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
      'Eén gesprek, in dertig seconden. Op de vraag hoe de maand verloopt en waar de ruimte nog zit, roept de agent tegelijkertijd vier alleen-lezen tools op: Month summary, Every category, Budget vs spent en Three months. De agent antwoordt dat Restaurants de enige categorie is die het budget overschrijdt: 166,50 uitgegeven van de beschikbare 144,00 (120,00 begroot + 24,00 overgebleven van eerdere maanden), 138,8 %, beschikbaar −22,50; dat de uitgaven van die categorie in drie maanden tijd zijn gestegen van 113,70 naar 119,90 naar 166,50; en dat er nog 80,00 over is bij Tennis en 411,90 bij Groceries. De agent stelt voor om de 22,50 te dekken uit de categorie Tennis, waar nog niets is uitgegeven. De gebruiker antwoordt ‘Cover it from Tennis.’, en move_money toont een voorbeeldweergave waarin niets verandert: budget van Tennis 80,00 → 57,50, budget van Restaurants 120,00 → 142,50, beschikbaar −22,50 → 0,00, precies binnen het budget, met een knop Cancel, een knop Confirm en de mededeling dat er niets verandert totdat u bevestigt en dat elke wijziging ongedaan kan worden gemaakt.',
    tour: 'Een rondleiding van 20 seconden door avenir-mcp: een vraag over een categorie die over budget is, vier tools die het plan gelijktijdig lezen, het exacte herstel in voorbeeld, bevestigd en ongedaan te maken, en de opdracht waarmee avenir-mcp wordt geïnstalleerd.',
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
