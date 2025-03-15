// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

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
			title: 'My Docs',
			social: {
				github: 'https://github.com/Qalisa/odoo-apps',
			},
			sidebar: [
				{
					label: 'Guides',
					items: [
						// Each item here is one entry in the navigation menu.
						{ label: 'Example Guide', slug: 'guides/example' },
					],
				},
				{
					label: 'Reference',
					autogenerate: { directory: 'reference' },
				},
			],
		}),
	],
});
