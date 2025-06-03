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
									label: 'Produits',
									autogenerate: { directory: 'by_job/gold_broker/product' },
								},
								{
									label: 'Vendre à un client',
									autogenerate: { directory: 'by_job/gold_broker/sell' },
								},
								{
									label: 'Rachat à un client',
									autogenerate: { directory: 'by_job/gold_broker/buy' },
								},
								{
									label: 'Comptabiliser les paiements',
									autogenerate: { directory: 'by_job/gold_broker/paying' },
								},
								{
									label: 'Bien utiliser les taxes',
									autogenerate: { directory: 'by_job/gold_broker/tax' },
								},
																{
									label: 'Avancé: Configuration',
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
