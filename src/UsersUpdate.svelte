<script>
    import * as urql from '@urql/svelte';

    export let id;
    export let username = '';
    export let email = '';
    export let firstName = '';
    export let lastName = '';

    let data = {id, username, email, firstName, lastName};

    urql.initClient({
        url: '/graphql',
    });

    const mutation = urql.mutation({query: `
        mutation updateUser(
            $id: ID!,
            $username: String,
            $email: String,
            $firstName: String,
            $lastName: String)
        {
            updateUser(
                data: {
                    username: $username,
                    email: $email,
                    firstName: $firstName,
                    lastName: $lastName
                },
                filters: {
                    id: { inList: [$id] }
                }
            ) {
                id
                username
                email
                firstName
                lastName
            }
        }
    `});

    function update(ev) {
        ev.preventDefault();
        const input = {id, username, email, firstName, lastName};
        mutation(input).then(result => {
            if (result.error) {
                console.log('ERROR', result.error);
            } else {
                data = result.data.updateUser[0];
            }
        });
    }
</script>

<style>
    form div {
        margin-bottom: 1em;
    }
</style>

<p>
Hello <em>{data.firstName} {data.lastName}</em>
</p>

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
        <button type="submit">Update</button>
    </div>
</form>
