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
					label: 'Gestion des clients',
					autogenerate: { directory: 'customers' },
				},
				{
					label: 'Produits',
					autogenerate: { directory: 'product' },
				},
				{
					label: 'Vendre à un client',
					autogenerate: { directory: 'sell' },
				},
				{
					label: 'Rachat à un client',
					autogenerate: { directory: 'buy' },
				},
				{
					label: 'Bien utiliser les taxes',
					autogenerate: { directory: 'tax' },
				}
			],
		}),
	],
});
