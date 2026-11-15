import {readFile,writeFile} from 'node:fs/promises';
import {applyDoorMeasurementPolicy} from '../lib/door-catalog.mjs';
const [input,output]=process.argv.slice(2);
const catalog=JSON.parse(await readFile(input));
await writeFile(output,JSON.stringify(applyDoorMeasurementPolicy(catalog)));
