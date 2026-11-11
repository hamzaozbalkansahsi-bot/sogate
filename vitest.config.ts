/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : vitest.config.ts
 * Açıklama   : Uygulamanın ilgili yapılandırmasını ve işlevini tanımlar.
 */
import { defineConfig } from 'vitest/config';
export default defineConfig({test:{environment:'node',include:['tests/unit/**/*.test.ts']}});
