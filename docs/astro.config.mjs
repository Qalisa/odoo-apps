// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { viewTransitions } from "astro-vtbot/starlight-view-transitions";

//
const site = (() => {
	let site = process.env.CANONICAL_URL // must be process.env and not import.meta.env
	if (site == null || site == "") return "http://localhost:4321"
	if (site.startsWith('http://') || site.startsWith('https://')) return site
	return 'https://' + site
})();

// https://astro.build/config
export default defineConfig({
	site,
	integrations: [
		starlight({
			title: 'Odoo - Procédures et Aide',
			locales: {
				root: {
					label: 'Français',
					lang: 'fr'
				},
			},

			logo: {
				src: './public/favicon.svg',
			},

			plugins: [viewTransitions()],

			social: {
				github: 'https://github.com/Qalisa/odoo-apps',
				linkedin: 'https://www.linkedin.com/company/qalisa',
			},
			sidebar: [
				{
					label: 'Accéder à Odoo',
					autogenerate: { directory: 'odoo' },
				},
				{
					label: 'Sauvegarde / Récupération des données',
					autogenerate: { directory: 'backups' },
				},
				{
					label: '⚙️ Pour les mainteneurs',
					autogenerate: { directory: 'maintainer' }
				},
				{
					label: "Par Métier",
					items: [
						{
							label: "🪙 Numismatique",
							items: [
								"by_job/gold_broker/introduction",
								{
									label: 'Gestion des clients',
									autogenerate: { directory: 'by_job/gold_broker/customers' },
								},
								{
									label: 'Gestion des Produits',
									autogenerate: { directory: 'by_job/gold_broker/product' },
								},
								{
									label: 'Devis (Acheter / Vendre)',
									autogenerate: { directory: 'by_job/gold_broker/estimate' },
								},
								{
									label: 'Factures, Paiements & Comptabilisation',
									autogenerate: { directory: 'by_job/gold_broker/invoice' },
								},
								{
									label: '🛠️ Configuration',
									autogenerate: { directory: 'by_job/gold_broker/configure' },
								}
							]
						},
					]
				},
			],
		}),
	],
});
