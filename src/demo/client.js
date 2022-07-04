import { readable } from 'svelte/store';
import * as urql from '@urql/svelte';

export const client = readable(
    urql.createClient({
        url: '/demo/graphql/',
    }),
);
