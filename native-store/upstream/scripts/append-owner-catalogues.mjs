import {readFile,writeFile} from 'node:fs/promises';
import {loadDoorCatalog,appendDoorCatalog} from '../lib/door-catalog.mjs';
import {loadFrontCatalog,appendFrontCatalog} from '../lib/cabinet-fronts.mjs';
const [root,input,output]=process.argv.slice(2);
const catalog=JSON.parse(await readFile(input)),doors=await loadDoorCatalog(root),fronts=await loadFrontCatalog(root);
appendDoorCatalog(catalog,doors.data,doors.version);appendFrontCatalog(catalog,fronts.data,fronts.version);
await writeFile(output,JSON.stringify(catalog));
console.log(JSON.stringify({products:catalog.products.length,doors:doors.data.products.length,fronts:fronts.data.products.length}));
