<script>
    import * as urql from '@urql/svelte';

    urql.initClient({
        url: '/graphql',
    });

    const users = urql.operationStore(`
        query {
            users {
                id
                username
                email
                firstName
                lastName
            }
        }
    `);

    urql.query(users);
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
        </tr>
        {#each $users.data.users as user}
        <tr>
            <td><a href="{user.id}/">{user.id}</a></td>
            <td>{user.username}</td>
            <td>{user.email}</td>
            <td>{user.firstName}</td>
            <td>{user.lastName}</td>
        </tr>
        {/each}
    </table>
</div>
{/if}
