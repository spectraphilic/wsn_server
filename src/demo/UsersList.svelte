<script>
    import * as urql from '@urql/svelte';
    import { client } from './client.js';

    let users = urql.queryStore({
        client: $client,
        query: urql.gql`
            query {
                users { id username email firstName lastName }
            }`,
    });

    let result;

    function remove(user) {
        result = urql.mutationStore({
            client: $client,
            variables: {id: user.id},
            query: urql.gql`
                mutation deleteUser($id: ID!) {
                    deleteUser(filters: {id: {exact: $id}})
                    { id }
                }
            `,
        });
    }

    $: if ($result && $result.fetching == false) {
        if ($result.error) {
            console.log('ERROR', $result.error);
        } else {
            const id = $result.data.deleteUser[0].id;
            console.log('DELETED', id);
        }
    }
</script>

<style>
    th, td {
        padding: 0 .5em;
    }
</style>

{#if $users.fetching}
    <p>Loading...</p>
{:else if $users.error}
    <p>Oh no... {$users.error.message}</p>
{:else}
<div>
    <table>
        <tr>
            <th>Id</th>
            <th>Username</th>
            <th>E-mail</th>
            <th>First name</th>
            <th>Last name</th>
            <th></th>
        </tr>
        {#each $users.data.users as user}
        <tr>
            <td><a href="{user.id}/">{user.id}</a></td>
            <td>{user.username}</td>
            <td>{user.email}</td>
            <td>{user.firstName}</td>
            <td>{user.lastName}</td>
            <td><button on:click|preventDefault={() => remove(user)}>Remove</button></td>
        </tr>
        {/each}
    </table>

    <p>
    <a href="create/">Add</a>
    </p>
</div>
{/if}
