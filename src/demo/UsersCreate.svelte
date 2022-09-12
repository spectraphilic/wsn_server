<script>
    import * as urql from '@urql/svelte';
    import { client } from './client.js';

    let id;
    let username = '';
    let email = '';
    let firstName = '';
    let lastName = '';

    let result;

    function update(ev) {
        ev.preventDefault();

        result = urql.mutationStore({
            client: $client,
            variables: {id, username, email, firstName, lastName},
            query: urql.gql`
                mutation createUser(
                    $username: String!,
                    $email: String,
                    $firstName: String,
                    $lastName: String)
                {
                    createUser(
                        data: {
                            username: $username,
                            email: $email,
                            firstName: $firstName,
                            lastName: $lastName
                        },
                    ) {
                        id
                        username
                        email
                        firstName
                        lastName
                    }
                }
            `,
        });
    }

    $: if ($result && $result.fetching == false) {
        if ($result.error) {
            console.log('ERROR', $result.error);
        } else {
            window.location.href = '..';
        }
    }
</script>

<style>
    form div {
        margin-bottom: 1em;
    }
</style>

<form on:submit={update}>
    <div>
        <label>
            Username<br>
            <input type="text" bind:value={username}>
        </label>
    </div>

    <div>
        <label>
            E-mail<br>
            <input type="text" bind:value={email}>
        </label>
    </div>

    <div>
        <label>
            First name<br>
            <input type="text" bind:value={firstName}>
        </label>
    </div>

    <div>
        <label>
            Last name<br>
            <input type="text" bind:value={lastName}>
        </label>
    </div>

    <div>
        <button type="submit">Create</button>
    </div>
</form>
